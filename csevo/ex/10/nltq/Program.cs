// 슬라이드 p10-v9-nullable9 — 제약 없는 T? 는 주석일 뿐, C# 9.0
using System;
using System.Reflection;

class App
{
    static T? Any<T>() => default;                    // C# 9
    static T? Val<T>() where T : struct => default;   // C# 2

    static void Show(string name, Type t)
    {
        MethodInfo m = typeof(App).GetMethod(name,
            BindingFlags.NonPublic | BindingFlags.Static)!
            .MakeGenericMethod(t);
        var ctx = new NullabilityInfoContext();
        var info = ctx.Create(m.ReturnParameter);
        object? r = m.Invoke(null, null);
        Console.WriteLine("{0}<{1}>: {2,-14} {3,-8} {4}", name, t.Name,
            m.ReturnType.Name, info.ReadState, r ?? "null");
    }

    static void Main()
    {
        Show("Any", typeof(string));
        Show("Any", typeof(int));
        Show("Val", typeof(int));
    }
}
