// 슬라이드 p8-v7-tasktype-own — 내가 만든 작업 같은 형식, C# 7.0
using System;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

// a task type: any class or struct that names its builder
[AsyncMethodBuilder(typeof(LogBuilder<>))]
public class Box<T>
{
    public T Value;
    public string Error;
}

class App
{
    static async Box<int> Answer()
    {
        await Task.CompletedTask;     // already complete: no suspension
        return 42;
    }

    static async Box<int> Fail()
    {
        await Task.CompletedTask;
        throw new InvalidOperationException("boom");
    }

    static void Main()
    {
        Console.WriteLine("Answer()");
        Box<int> a = Answer();
        Console.WriteLine("Value = " + a.Value);
        Console.WriteLine("Fail()");
        Box<int> f = Fail();
        Console.WriteLine("Error = " + f.Error);
    }
}
