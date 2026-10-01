// 슬라이드 p3-v2-iterator-later — 반복기 안의 ref 지역 변수, C# 13
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Bump(int[] xs)
    {
        for (int i = 0; i < xs.Length; i++)
        {
            ref int slot = ref xs[i];     // no yield while it is alive
            slot += 10;
        }
        yield return xs[0];
    }

    static void Main()
    {
        int[] xs = new int[] { 1, 2 };
        foreach (int x in Bump(xs)) Console.WriteLine(x);
    }
}
