// 슬라이드 p7-v6-nameof-const — 컴파일 시간 상수, C# 6.0
using System;
using System.Linq.Expressions;

class App
{
    const string Key = nameof(Key);                  // const field

    [Obsolete("use " + nameof(Run) + " instead")]    // attribute
    static void OldRun() { }
    static void Run() { }

    static string Describe(string field)
    {
        switch (field)
        {
            case nameof(Key): return "the key";      // case label
            case nameof(Run): return "a method";
            default: return "?";
        }
    }

    static void Main()
    {
        Console.WriteLine(Key);
        Console.WriteLine(Describe("Key") + ", " + Describe("Run"));
        Expression<Func<string>> e = () => nameof(Main);
        Console.WriteLine(e.Body.NodeType + ": " + e.Body);
        object a = typeof(App).GetMethod("OldRun",
            System.Reflection.BindingFlags.NonPublic |
            System.Reflection.BindingFlags.Static)
            .GetCustomAttributes(typeof(ObsoleteAttribute), false)[0];
        Console.WriteLine(((ObsoleteAttribute)a).Message);
    }
}
