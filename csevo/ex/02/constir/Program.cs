// 슬라이드 p2-v1-constir — const·readonly 의 메타데이터, C# 1.0
using System;
using System.Reflection;

class Config
{
    public const int Max = 3;
    public static readonly int Limit = 3;
    public readonly int Id = 1;
}

class App
{
    static void Show(string name)
    {
        BindingFlags all = BindingFlags.Public | BindingFlags.Static
            | BindingFlags.Instance;
        FieldInfo f = typeof(Config).GetField(name, all);
        Console.WriteLine(name + ": static=" + f.IsStatic
            + " literal=" + f.IsLiteral + " initonly=" + f.IsInitOnly);
    }

    static void Main()
    {
        Show("Max");
        Show("Limit");
        Show("Id");
        FieldInfo max = typeof(Config).GetField("Max");
        Console.WriteLine("value from metadata: " + max.GetValue(null));
    }
}
