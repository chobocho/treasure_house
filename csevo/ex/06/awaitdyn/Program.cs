// 슬라이드 p6-v5-awaitdyn — dynamic 도 await 할 수 있다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<string> Demo(dynamic d)
    {
        object r = await d;             // checked at run time
        return "awaited " + r;
    }

    static void Main()
    {
        Console.WriteLine(Demo(Task.FromResult(7)).Result);
        try { Console.WriteLine(Demo("text").Result); }
        catch (AggregateException e)
        {
            Console.WriteLine(e.InnerException.GetType().Name);
            Console.WriteLine(e.InnerException.Message);
        }
    }
}
