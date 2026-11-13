cmake_minimum_required(VERSION 3.16) # theo chuẩn quốc tế -> cần khai báo đầu tiên

set(EXTRA_COMPONENT_DIRS "../shared") # lấy component của folder shared và lấy crycare_protocol.h

include($ENV{IDF_PATH}/tools/cmake/project.cmake) # $ENV{IDF_PATH} đường dẫn của Espressif -> project.cmake nạp trình biên dịch của ESP32 , ...

project(s3_listener) # đặt tên cho các file nhị phân như s3_listener.elf và s3_listener.bin