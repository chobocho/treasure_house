// 슬라이드 p5-v4-opt-after — 메서드 하나와 기본값, C# 4.0
using System;

class Program
{
    static void Save(string path, bool overwrite = false,
                     int buffer = 4096)
    {
        Console.WriteLine(path + " overwrite=" + overwrite
                          + " buffer=" + buffer);
    }

    static void Main()
    {
        Save("a.txt");
        Save("b.txt", true);
        Save("c.txt", buffer: 512);  // skip the middle one
    }
}
