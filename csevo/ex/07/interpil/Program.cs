// 슬라이드 p7-v6-interp-il — 보간 문자열은 무엇을 부르나, C# 6.0
using System;
using System.Reflection;

class App
{
    static string Obj(object a, int b) { return $"{a}-{b}"; }
    static string Fmt(int a) { return $"{a,5:X}"; }
    static string Str(string a, string b) { return $"{a}-{b}"; }
    static FormattableString Fs(int a) { return $"{a}"; }
    static string Old(object a, int b)
    {
        return string.Format("{0}-{1}", a, b);
    }

    static void Main()
    {
        string[] names = { "Obj", "Fmt", "Str", "Fs", "Old" };
        foreach (string name in names)
        {
            Console.WriteLine(name + ":");
            Il.Calls(typeof(App).GetMethod(name,
                BindingFlags.NonPublic | BindingFlags.Static));
        }
    }
}
