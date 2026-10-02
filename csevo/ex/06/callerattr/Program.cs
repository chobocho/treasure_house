// 슬라이드 p6-v5-caller-attr — 특성 인자와 partial 메서드, C# 5.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

class TagAttribute : Attribute
{
    public readonly string Where;
    public TagAttribute([CallerMemberName] string m = "?",
        [CallerLineNumber] int line = 0)
    {
        Where = m + " line " + line;
    }
}

partial class Job
{
    // Only the defining declaration's attributes count.
    partial void Log(string msg, [CallerMemberName] string m = "?");
    partial void Log(string msg, string m)
    {
        Console.WriteLine("partial: " + msg + " <- " + m);
    }
    public void Run() { Log("run"); }
}

class App
{
    [Tag] public static void Save() { }
    [Tag] public int Size { get; set; }

    static void Main()
    {
        MemberInfo[] ms = { typeof(App).GetMethod("Save"),
                            typeof(App).GetProperty("Size") };
        foreach (MemberInfo m in ms)
            Console.WriteLine("attribute: " + m.GetCustomAttribute<
                TagAttribute>().Where);
        new Job().Run();
    }
}
