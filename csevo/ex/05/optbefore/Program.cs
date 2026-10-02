// 슬라이드 p5-v4-opt-before — 이전엔 오버로드 사슬, C# 3.0
using System;

class Program
{
    static void Save(string path)
    {
        Save(path, false);
    }

    static void Save(string path, bool overwrite)
    {
        Save(path, overwrite, 4096);
    }

    static void Save(string path, bool overwrite, int buffer)
    {
        Console.WriteLine(path + " overwrite=" + overwrite
                          + " buffer=" + buffer);
    }

    static void Main()
    {
        Save("a.txt");
        Save("b.txt", true);
        Save("c.txt", false, 512);   // must repeat the middle default
    }
}
