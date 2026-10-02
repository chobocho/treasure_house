// 슬라이드 p10-v9-localsinit — [SkipLocalsInit], C# 9.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static int Normal()
    {
        Span<int> s = stackalloc int[4];
        return s.Length;
    }

    [SkipLocalsInit]
    static int Skipped()
    {
        Span<int> s = stackalloc int[4];
        return s.Length;
    }

    static void Main()
    {
        BindingFlags f = BindingFlags.Static | BindingFlags.NonPublic;
        foreach (string n in new[] { "Normal", "Skipped" })
        {
            MethodBody b = typeof(App).GetMethod(n, f).GetMethodBody();
            Console.WriteLine(n + ": InitLocals " + b.InitLocals
                + ", IL locals " + b.LocalVariables.Count);
        }
    }
}
