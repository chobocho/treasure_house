// 슬라이드 p12-v11-lp-later12 — 컬렉션 식과 목록 패턴, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        int[] head = [1, 2];
        int[] all = [.. head, 3, 4];        // C# 12: build
        if (all is [1, 2, .. var tail])      // C# 11: take apart
        {
            Console.WriteLine(string.Join(",", tail));
            List<int> list = [.. tail, .. head];
            Console.WriteLine(list is [3, 4, 1, 2]);
        }

        int[] none = [];
        Console.WriteLine(none is []);
    }
}
