// 슬라이드 p8-v7_3-unmanaged-meta — unmanaged 제약의 메타데이터, C# 7.3
using System;
using System.Linq;

class App
{
    static void U<T>() where T : unmanaged { }
    static void S<T>() where T : struct { }

    static void Show(string name)
    {
        var t = typeof(App).GetMethod(name,
            System.Reflection.BindingFlags.NonPublic
            | System.Reflection.BindingFlags.Static)
            .GetGenericArguments()[0];
        var attrs = t.GetCustomAttributes(false)
                     .Select(a => a.GetType().Name);
        var cons = t.GetGenericParameterConstraints()
                    .Select(c => c.Name);
        Console.WriteLine(name + ": " + t.GenericParameterAttributes);
        Console.WriteLine("   constraints=[" + string.Join(",", cons)
            + "] attrs=[" + string.Join(",", attrs) + "]");
    }

    static void Main()
    {
        Show("U");
        Show("S");
    }
}
