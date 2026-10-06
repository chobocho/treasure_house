// 슬라이드 p13-v12-ce-lower — 컴파일러가 만든 코드를 IL 로 본다, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static int[] Concat(int[] xs, int[] ys) => [.. xs, .. ys];

    static List<int> AddZero(List<int> xs) => [.. xs, 0];

    static int[] FromSeq(IEnumerable<int> e) => [.. e];

    static ReadOnlySpan<int> Consts() => [1, 2, 3];

    static int Vars(int a, int b)
    {
        Span<int> s = [a, b];
        return s[0] + s[1];
    }

    static void Main()
    {
        Il.Calls("Concat");
        Il.Calls("AddZero");
        Il.Calls("FromSeq");
        Il.Calls("Consts");
        Il.Calls("Vars");
    }
}
