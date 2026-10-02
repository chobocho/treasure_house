// 슬라이드 p8-v7-locfn-delegate — 대리자로 바꾸면 다시 클래스, C# 7.0
using System;
using System.Linq;
using System.Reflection;

class App
{
    static Func<int, int> MakeAdder(int k)
    {
        return Add;                     // local function -> delegate
        int Add(int x) => x + k;
    }

    static void Main()
    {
        var add = MakeAdder(10);
        Console.WriteLine(add(1));
        Console.WriteLine(add.Target.GetType().Name + " struct="
            + add.Target.GetType().IsValueType);
        Console.WriteLine(add.Method.Name);
        var nested = typeof(App).GetNestedTypes(BindingFlags.NonPublic);
        foreach (var t in nested.OrderBy(t => t.Name))
            Console.WriteLine(t.Name + " struct=" + t.IsValueType);
    }
}
