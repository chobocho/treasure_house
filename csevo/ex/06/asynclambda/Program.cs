// 슬라이드 p6-v5-lambda — async 람다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static void Main()
    {
        // expression body: the int result is wrapped in Task<int>
        Func<int, Task<int>> twice =
            async x => await Task.FromResult(x * 2);

        // block body without return: Task
        Func<string, Task> print = async s =>
        {
            await Task.FromResult(0);
            Console.WriteLine("print: " + s);
        };

        // an async anonymous method (C# 2 syntax) works too
        Func<Task<string>> hello = async delegate
        {
            return await Task.FromResult("hello");
        };

        print("x").Wait();
        Console.WriteLine(twice(21).Result + " " + hello().Result);
    }
}
