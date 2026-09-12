// -*- coding: utf-8 -*-
// compresslib 명령줄 도구 (C++) — 다섯 언어가 같은 사용법을 갖는다.
//
//     cppcli <알고리즘> enc|dec <입력> <출력>
//     cppcli batch <작업파일>
//     cppcli list
//
// batch 가 있는 이유는 파서티 검사다. (알고리즘 × 파일 × 언어) 조합이
// 수천 건이라 건마다 프로세스를 띄우면 JVM 하나로 몇 분이 간다.
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "../../src/cpp/registry.h"

using compresslib::Bytes;
namespace registry = compresslib::registry;

static bool read_file(const std::string& path, Bytes& out) {
  std::ifstream f(path, std::ios::binary);
  if (!f) return false;
  out.assign(std::istreambuf_iterator<char>(f),
             std::istreambuf_iterator<char>());
  return true;
}

static bool write_file(const std::string& path, const Bytes& data) {
  std::ofstream f(path, std::ios::binary);
  if (!f) return false;
  if (!data.empty())
    f.write(reinterpret_cast<const char*>(data.data()),
            static_cast<std::streamsize>(data.size()));
  return f.good();
}

// 실패하면 사람이 읽을 문장을, 성공하면 빈 문자열을 돌려준다.
static std::string run_one(const std::string& algo,
                           const std::string& mode,
                           const std::string& in,
                           const std::string& out) {
  const registry::Entry* e = registry::find(algo);
  if (!e) return "모르는 알고리즘: " + algo;
  if (mode != "enc" && mode != "dec")
    return "enc 또는 dec 이어야 한다: " + mode;
  Bytes data;
  if (!read_file(in, data)) return "입력을 못 읽는다: " + in;
  Bytes result;
  try {
    result = (mode == "enc") ? e->encode(data) : e->decode(data);
  } catch (const std::exception& ex) {
    return algo + " " + mode + " 실패: " + ex.what();
  }
  if (!write_file(out, result)) return "출력을 못 쓴다: " + out;
  return std::string();
}

static int batch(const std::string& job_path) {
  std::ifstream f(job_path);
  if (!f) {
    std::cerr << "작업 파일을 못 읽는다: " << job_path << "\n";
    return 2;
  }
  std::string line;
  while (std::getline(f, line)) {
    if (line.empty() || line[0] == '#') continue;
    std::istringstream ss(line);
    std::string algo, mode, in, out, extra;
    if (!(ss >> algo >> mode >> in >> out) || (ss >> extra)) {
      std::cout << "FAIL 칸이 4개가 아니다\n";
      continue;
    }
    std::string err = run_one(algo, mode, in, out);
    std::cout << (err.empty() ? "OK" : "FAIL " + err) << "\n";
  }
  return 0;
}

int main(int argc, char** argv) {
  std::vector<std::string> args(argv + 1, argv + argc);
  if (args.size() == 1 && args[0] == "list") {
    for (const auto& e : registry::entries())
      std::cout << e.name << "\n";
    return 0;
  }
  if (args.size() == 2 && args[0] == "batch") return batch(args[1]);
  if (args.size() != 4) {
    std::cerr << "사용법: cppcli <알고리즘> enc|dec <입력> <출력>\n"
                 "        cppcli batch <작업파일>\n";
    return 2;
  }
  std::string err = run_one(args[0], args[1], args[2], args[3]);
  if (!err.empty()) {
    std::cerr << err << "\n";
    return 1;
  }
  return 0;
}
