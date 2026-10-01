// 슬라이드 p2-v1-explicitfail — 명시적 구현은 숨는다, C# 1.0
using System;
using System.Reflection;

interface ILog { void Write(string s); }

class FileLog : ILog
{
    void ILog.Write(string s) { Console.WriteLine("log: " + s); }
}

class App
{
    static void Main()
    {
        FileLog f = new FileLog();
        ((ILog)f).Write("via ILog");     // f.Write(...) won't compile

        Type t = typeof(FileLog);
        bool none = t.GetMethod("Write") == null;
        Console.WriteLine("public Write missing: " + none);
        BindingFlags all = BindingFlags.Instance
            | BindingFlags.NonPublic | BindingFlags.DeclaredOnly;
        foreach (MethodInfo m in t.GetMethods(all))
            Console.WriteLine("declared: " + m.Name + " private="
                + m.IsPrivate + " virtual=" + m.IsVirtual
                + " final=" + m.IsFinal);
    }
}
