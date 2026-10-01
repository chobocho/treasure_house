// 슬라이드 p6-v5-noawait — await 없는 async 메서드, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    // no await at all
    static async Task<int> Square(int x)
    {
        Console.WriteLine("Square: computing");
        return x * x;
    }

    static void Main()
    {
        Task<int> t = Square(7);
        Console.WriteLine("Main: " + t.Status + ", " + t.Result);
    }
}
