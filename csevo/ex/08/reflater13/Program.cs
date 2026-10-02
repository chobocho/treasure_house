// 슬라이드 p8-v7-ref-later13 — async·반복기 안의 ref 지역 변수, C# 13
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static int[] data = { 1, 2, 3 };

    static async Task<int> Async()
    {
        await Task.Yield();
        ref int r = ref data[0];   // allowed: no await while r lives
        r += 10;
        return r;
    }

    static IEnumerable<int> Iter()
    {
        for (int i = 0; i < data.Length; i++)
        {
            ref int r = ref data[i];  // no yield while r lives
            r *= 2;
            yield return data[i];
        }
    }

    static void Main()
    {
        Console.WriteLine(Async().Result);
        Console.WriteLine(string.Join(",", Iter()));
    }
}
