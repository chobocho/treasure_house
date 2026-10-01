// 슬라이드 p2-v1-cctor — 정적 생성자는 처음 쓸 때 한 번, C# 1.0
using System;

class Config
{
    public static string Name = Trace("static field initializer");

    static Config()
    {
        Trace("static constructor");
        Name = Name + " + ctor";
    }

    public Config() { Trace("instance constructor"); }

    static string Trace(string s)
    {
        Console.WriteLine("  " + s);
        return "init";
    }
}

class App
{
    static void Main()
    {
        Console.WriteLine("Main starts");
        Console.WriteLine("first use:");
        Console.WriteLine("  Name = " + Config.Name);
        Console.WriteLine("second use:");
        new Config();
        new Config();
    }
}
