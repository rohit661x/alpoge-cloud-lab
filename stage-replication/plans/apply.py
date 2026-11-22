"""Generate the controller used by the three-arm driver from pinned upstream."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap

HERE = Path(__file__).resolve().parent
PIN = 'ff6beb5d36465ed06071fff1e4adfea0a0daf4a771c2470541decd38cb2fd0d0'


def transform(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('FHEController.cpp differs from pinned upstream')
    original = raw.decode()
    with tempfile.TemporaryDirectory() as folder:
        copy = Path(folder) / 'FHEController.cpp'
        copy.write_bytes(raw)
        subprocess.run(['patch', '-s', str(copy), str(HERE / 'reuse.patch')], check=True)
        four = copy.read_text()

    def dispatch(source, begin, end, original_part, four_part, three_part=None):
        index = source.index(begin)
        stop = source.index(end, index)
        cases = [('if (stage_plan::selected().arm == stage_plan::Arm::original)', original_part)]
        if three_part:
            cases.append(('else if (stage_plan::selected().arm == stage_plan::Arm::four)', four_part))
            cases.append(('else', three_part))
        else:
            cases.append(('else', four_part))
        body = ' '.join(condition + ' {\n' + textwrap.indent(textwrap.dedent(block).strip('\n'), '        ') + '\n    }'
                        for condition, block in cases)
        return source[:index] + '    ' + body + '\n\n' + source[stop:]

    result = original
    for signature in ('Ctxt FHEController::convbn_initial(', 'Ctxt FHEController::convbn('):
        start = result.index(signature)
        fragment = result[start:result.index('\n}', start)]
        four_start = four.index(signature)
        four_fragment = four[four_start:four.index('\n}', four_start)]
        def slice_body(source, first, last):
            return source[source.index(first):source.index(last)]
        begin, end = '    int img_width', '    Ptxt bias'
        updated = dispatch(fragment, begin, end, slice_body(fragment, begin, end),
                           slice_body(four_fragment, begin, end),
                           'c_rotations = stage_plan::three_views(context, in);')
        if 'convbn_initial' in signature:
            begin, end = '        res = add(res, context->EvalRotate(sum, 1024));', '        res = mult(res, mask_from_to'
            updated = dispatch(updated, begin, end, slice_body(fragment, begin, end),
                               slice_body(four_fragment, '        auto next_channel', end))
            updated = updated.replace('    generate_rotation_keys({1024});\n', '')
        result = result.replace(fragment, updated, 1)
    return result.replace('#include "FHEController.h"', '#include "stage_plan.hpp"', 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(transform(args.input))
    dest = args.output.parent / 'stage_plan.hpp'
    if dest.resolve() != HERE / 'stage_plan.hpp':
        shutil.copyfile(HERE / 'stage_plan.hpp', dest)
