// 슬라이드 p13-v12-ce-over2 — 스팬·List·IEnumerable 사이, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static void A(ReadOnlySpan<int> s) { Console.WriteLine("A ROS"); }
    static void A(Span<int> s) { Console.WriteLine("A Span"); }

    static void B(IEnumerable<int> e) { Console.WriteLine("B IEnum"); }
    static void B(List<int> l) { Console.WriteLine("B List"); }

    static void C(int[] a) { Console.WriteLine("C int[]"); }
    static void C(IEnumerable<int> e) { Console.WriteLine("C IEnum"); }

    static void D(ReadOnlySpan<int> s) { Console.WriteLine("D ROS"); }
    static void D(List<int> l) { Console.WriteLine("D List"); }

    static void Main()
    {
        A([1, 2]);
        B([1, 2]);
        C([1, 2]);
#if BAD
        D([1, 2]);
#endif
    }
}
