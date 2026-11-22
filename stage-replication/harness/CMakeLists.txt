cmake_minimum_required(VERSION 3.16)
project(native_stage LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(OpenFHE CONFIG REQUIRED)
find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(APP "${CMAKE_CURRENT_SOURCE_DIR}/../app" CACHE PATH "Pinned ResNet20 checkout")
set(PLANS "${CMAKE_CURRENT_SOURCE_DIR}/../plans" CACHE PATH "Native rotation-plan source")
add_custom_command(OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/FHEController.cpp" "${CMAKE_CURRENT_BINARY_DIR}/stage_plan.hpp"
  COMMAND "${Python3_EXECUTABLE}" "${PLANS}/apply.py" "${APP}/src/FHEController.cpp" "${CMAKE_CURRENT_BINARY_DIR}/FHEController.cpp"
  DEPENDS "${PLANS}/apply.py" "${PLANS}/reuse.patch" "${PLANS}/stage_plan.hpp" "${APP}/src/FHEController.cpp"
  VERBATIM)
add_executable(stage_native stage.cpp "${CMAKE_CURRENT_BINARY_DIR}/FHEController.cpp" "${CMAKE_CURRENT_BINARY_DIR}/stage_plan.hpp")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenFHE_CXX_FLAGS}")
target_include_directories(stage_native PRIVATE "${APP}/src" "${CMAKE_CURRENT_BINARY_DIR}" ${OPENMP_INCLUDES} "${OpenFHE_INCLUDE}" "${OpenFHE_INCLUDE}/third-party/include" "${OpenFHE_INCLUDE}/core" "${OpenFHE_INCLUDE}/pke" "${OpenFHE_INCLUDE}/binfhe")
target_link_directories(stage_native PRIVATE "${OpenFHE_LIBDIR}")
target_link_libraries(stage_native PRIVATE ${OpenFHE_SHARED_LIBRARIES})
