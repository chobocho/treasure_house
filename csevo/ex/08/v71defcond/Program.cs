// 슬라이드 p8-v7_1-default-cond — ?: 안의 default, C# 7.1
using System;

class App
{
    static int? A(bool ok) => ok ? 1 : default;           // int 0
    static int? B(bool ok) => ok ? 1 : default(int?);     // null
    static int? C(bool ok) => ok ? (int?)1 : default;     // null
    static int? D(bool ok) { if (ok) return 1; return default; }

    static string Show(int? v) => v.HasValue ? v.ToString() : "null";

    static void Main()
    {
        Console.WriteLine("A " + Show(A(false)));
        Console.WriteLine("B " + Show(B(false)));
        Console.WriteLine("C " + Show(C(false)));
        Console.WriteLine("D " + Show(D(false)));
    }
}
