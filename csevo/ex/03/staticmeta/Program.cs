// 슬라이드 p3-v2-static-meta — 메타데이터의 static 클래스, C# 2.0
using System;
using System.Reflection;

static class Util { public static int One() { return 1; } }

sealed class OldUtil                 // the C# 1 way
{
    private OldUtil() { }
    public static int One() { return 1; }
}

class App
{
    static void Show(Type t)
    {
        BindingFlags all = BindingFlags.Public | BindingFlags.NonPublic
                         | BindingFlags.Instance;
        Console.WriteLine(t.Name + ": abstract " + t.IsAbstract
            + ", sealed " + t.IsSealed
            + ", constructors " + t.GetConstructors(all).Length);
    }

    static void Main()
    {
        Show(typeof(Util));
        Show(typeof(OldUtil));
    }
}
