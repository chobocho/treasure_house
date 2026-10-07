// 슬라이드 p15-v14-fk-static — 정적 속성과 인터페이스의 field, C# 14
using System;
using System.Reflection;

interface ISettings
{
    static string Mode { get; set => field = value.ToLower(); }
#if IFACE
    string Name { get; set => field = value; }
#endif
}

class Config
{
    public static int Port
    { get; set => field = value > 0 ? value : 80; }
}

class Program
{
    static void Main()
    {
        Config.Port = -1;
        ISettings.Mode = "FAST";
        Console.WriteLine(Config.Port + " " + ISettings.Mode);
        var flags = BindingFlags.NonPublic | BindingFlags.Static;
        Console.WriteLine(typeof(ISettings).GetFields(flags)[0].Name);
        Console.WriteLine(typeof(Config).GetFields(flags)[0].Name);
    }
}
