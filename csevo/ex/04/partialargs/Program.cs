// 슬라이드 p4-v3-partial-args — 구현 없으면 인자째 사라진다, C# 3.0
using System;
using System.Reflection;

partial class Doc
{
    partial void OnLog(string msg);       // defining declaration (tool)

    public void Save()
    {
        OnLog(Expensive("saving"));
        Console.WriteLine("saved");
    }

    static string Expensive(string s)
    {
        Console.WriteLine("Expensive(\"" + s + "\") ran");
        return s;
    }
}

#if IMPL
partial class Doc
{
    partial void OnLog(string msg) { Console.WriteLine("log: " + msg); }
}
#endif

class App
{
    static void Main()
    {
        new Doc().Save();
        MethodInfo m = typeof(Doc).GetMethod("OnLog",
            BindingFlags.NonPublic | BindingFlags.Instance);
        Console.WriteLine("OnLog in the assembly: " + (m != null));
    }
}
