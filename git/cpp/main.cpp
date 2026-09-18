// mygit 명령 — run() 을 진짜 표준 스트림에 잇는다.
#include <iostream>

#include "mygit.hpp"

int main(int argc, char** argv) {
    auto r = mygit::run({argv + 1, argv + argc}, "", mygit::os_env(),
                        std::nullopt);
    std::cout << r.out;
    std::cerr << r.err;
    return r.code;
}
