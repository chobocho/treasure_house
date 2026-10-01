// 슬라이드 p4-v3-ext-static — 확장 메서드는 그냥 정적 메서드다, C# 3.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

static class IntExt
{
    public static bool IsEven(this int n) { return n % 2 == 0; }
}

class App
{
    static void Main()
    {
        Console.WriteLine(4.IsEven() + " " + IntExt.IsEven(4));

        MethodInfo m = typeof(IntExt).GetMethod("IsEven");
        Console.WriteLine("static: " + m.IsStatic
            + ", parameters: " + m.GetParameters().Length);
        Type ext = typeof(ExtensionAttribute);
        Console.WriteLine("[Extension] on method:   "
            + m.IsDefined(ext, false));
        Console.WriteLine("[Extension] on class:    "
            + typeof(IntExt).IsDefined(ext, false));
        Console.WriteLine("[Extension] on assembly: "
            + typeof(App).Assembly.IsDefined(ext));
    }
}
