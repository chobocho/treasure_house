// 슬라이드 p9-v8-range-prec — .. 는 + 보다 먼저 묶인다, C# 8.0
using System;

class App
{
    static void Main()
    {
        int[] a = { 0, 1, 2, 3, 4, 5, 6 };
        int i = 2;
        // parentheses around the arithmetic are required
        int[] s = a[i..(i + 3)];
        Console.WriteLine(string.Join(",", s));
        // unary operators bind tighter than ..
        Console.WriteLine(string.Join(",", a[^3..]));
#if BAD
        int[] t = a[i..i + 3];       // means (i..i) + 3
#endif
    }
}
