// 슬라이드 p8-v7-ref-where — ref 지역 변수를 못 쓰는 곳, C# 7.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static int[] data = { 1, 2, 3 };

    static void Lambda()
    {
        ref int r = ref data[0];
        Func<int> f = () => r;           // captured by a closure
    }

    static async Task Async()
    {
        ref int r = ref data[0];         // in an async method
        await Task.Yield();
    }

    static IEnumerable<int> Iter()
    {
        ref int r = ref data[0];         // in an iterator
        yield return 1;
    }

    static void Main()
    {
    }
}
