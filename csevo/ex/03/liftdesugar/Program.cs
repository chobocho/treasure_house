// 슬라이드 p3-v2-lifted-lowering — 끌어올린 + 를 풀어 쓰면, C# 2.0
using System;

class App
{
    static int? Lifted(int? a, int? b)
    {
        return a + b;
    }

    static int? ByHand(int? a, int? b)
    {
        if (a.HasValue && b.HasValue)
        {
            int sum = a.GetValueOrDefault() + b.GetValueOrDefault();
            return new int?(sum);
        }
        return new int?();                // the null value
    }

    static string S(int? v)
    {
        return v.HasValue ? v.Value.ToString() : "null";
    }

    static void Main()
    {
        int?[] xs = new int?[] { 1, null };
        foreach (int? a in xs)
        {
            foreach (int? b in xs)
            {
                Console.WriteLine(S(a) + " + " + S(b) + " = "
                    + S(Lifted(a, b)) + " / " + S(ByHand(a, b)));
            }
        }
    }
}
