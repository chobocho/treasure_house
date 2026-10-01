// 슬라이드 p3-v2-anon-async — async 익명 메서드, C# 5.0
using System;
using System.Threading.Tasks;

delegate Task<int> AsyncOp(int x);

class App
{
    static void Main()
    {
        AsyncOp twice = async delegate(int x)
        {
            await Task.Yield();
            return x * 2;
        };
        Console.WriteLine(twice(21).Result);
    }
}
