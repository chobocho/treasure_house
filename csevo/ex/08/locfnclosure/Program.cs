// 슬라이드 p8-v7-locfn-closure — 포착 변수는 어디에 사나, C# 7.0
using System;
using System.Linq;
using System.Reflection;

class App
{
    static int ByLambda(int k)
    {
        Func<int, int> add = x => x + k;    // captures k
        return add(1);
    }

    static int ByLocal(int k)
    {
        return Add(1);
        int Add(int x) => x + k;            // captures k
    }

    static void Main()
    {
        Console.WriteLine(ByLambda(1) + ByLocal(2));
        // compiler-generated nested types: an implementation detail
        var nested = typeof(App).GetNestedTypes(BindingFlags.NonPublic);
        foreach (var t in nested.OrderBy(t => t.Name))
            Console.WriteLine("{0,-22} {1,-6} fields: {2}", t.Name,
                t.IsValueType ? "struct" : "class",
                string.Join(",", t.GetFields().Select(f => f.Name)));
    }
}
