// 슬라이드 p12-v11-math-ops — TSelf·TOther·TResult 세 자리, C# 11.0
using System;
using System.Linq;
using System.Numerics;

// A user type: Day + int -> Day (TOther is not Day)
struct Day : IAdditionOperators<Day, int, Day>
{
    public int N;
    public static Day operator +(Day d, int k) =>
        new Day { N = d.N + k };
}

class App
{
    static T Step<T, TD>(T start, TD by, int n)
        where T : IAdditionOperators<T, TD, T>
    {
        T x = start;
        for (int i = 0; i < n; i++) x += by;
        return x;
    }

    static void Main()
    {
        Console.WriteLine(Step(10, 5, 3) + " "
            + Step(new Day(), 7, 2).N);
        // Non-generic CoreLib value types that implement it
        Type g = typeof(IAdditionOperators<,,>);
        var rows = typeof(object).Assembly.GetExportedTypes()
            .Where(t => t.IsValueType && !t.IsGenericType)
            .SelectMany(t => t.GetInterfaces()
                .Where(i => i.IsGenericType
                    && i.GetGenericTypeDefinition() == g)
                .Select(i => (t, o: i.GetGenericArguments()[1])))
            .OrderBy(r => r.t.Name, StringComparer.Ordinal).ToArray();
        Console.WriteLine(rows.Length + " types, TOther == TSelf: "
            + rows.Count(r => r.o == r.t));
        for (int i = 0; i < rows.Length; i += 9)
            Console.WriteLine("  " + string.Join(" ",
                rows.Skip(i).Take(9).Select(r => r.t.Name)));
        Console.WriteLine("DateTime: "
            + typeof(DateTime).GetInterfaces()
            .Count(i => i.Namespace == "System.Numerics"));
    }
}
