// 슬라이드 p2-v1-nothrows — 검사 예외가 없다, C# 1.0
using System;
using System.IO;

class Config
{
    // No 'throws' clause: nothing tells the caller about this.
    public static string Load(string path)
    {
        if (!File.Exists(path))
            throw new FileNotFoundException("no config", path);
        return "...";
    }
}

class App
{
    static void Main()
    {
        string s = Config.Load("missing.cfg");   // no try required
        Console.WriteLine(s);
    }
}
