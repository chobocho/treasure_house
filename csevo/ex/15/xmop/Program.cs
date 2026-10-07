// 슬라이드 p15-v14-ext-op — 남의 형식에 연산자를 붙인다, C# 14
using System;
using System.Linq;
using System.Numerics;

static class VecOps
{
    extension<T>(T[]) where T : INumber<T>
    {
        public static T[] operator *(T[] v, T k) =>
            v.Select(x => x * k).ToArray();
        public static T[] operator *(T k, T[] v) => v * k;
        public static T[] operator +(T[] a, T[] b) =>
            a.Zip(b, (x, y) => x + y).ToArray();
        public static bool operator true(T[] v) => v.Length > 0;
        public static bool operator false(T[] v) => v.Length == 0;
    }
}

class Program
{
    static string Show<T>(T[] v) => "[" + string.Join(", ", v) + "]";

    static void Main()
    {
        int[] a = { 1, 2, 3 };
        double[] d = { 0.5, 1.5 };
        Console.WriteLine(Show(a * 10) + " " + Show(2.0 * d));
        Console.WriteLine(Show(a + new[] { 10, 20, 30 }));
        Console.WriteLine(new int[0] ? "non-empty" : "empty");
        Console.WriteLine(Show(VecOps.op_Multiply(a, 3)));
#if STR
        Console.WriteLine(new[] { "x" } * "y");     // T : INumber<T>
#endif
    }
}
