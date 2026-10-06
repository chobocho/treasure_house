// 슬라이드 p14-v13-ru-async — async 메서드의 unsafe, C# 13.0
using System;
using System.Threading.Tasks;

class App
{
    static int[] data = { 5, 6, 7 };

    static async Task<int> Third()
    {
        await Task.Yield();
        int v;
        unsafe
        {
            fixed (int* p = data) { v = p[2]; }
#if AWAIT
            await Task.Yield();        // await inside unsafe
#elif ADDR
            int* q = &v;               // address of a local
#endif
        }
        return v;
    }

    static void Main() => Console.WriteLine(Third().Result);
}
