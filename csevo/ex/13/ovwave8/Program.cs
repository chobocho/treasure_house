// 슬라이드 p13-v12-wave8 — 경고 웨이브 8 의 CS9123, C# 12.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> Work()
    {
        int local = 41;
        unsafe
        {
            int* p = &local;      // address of a local in async
            *p += 1;
        }
        await Task.Yield();       // local may now live on the heap
        return local;
    }

    static void Main() => Console.WriteLine(Work().Result);
}
