// 슬라이드 p6-v5-critical — ICriticalNotifyCompletion 이면, C# 5.0
using System;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class Plain : INotifyCompletion
{
    public Plain GetAwaiter() { return this; }
    public bool IsCompleted { get { return false; } }
    public void OnCompleted(Action k)
    { Console.WriteLine("Plain: OnCompleted"); k(); }
    public void GetResult() { }
}

class Critical : ICriticalNotifyCompletion
{
    public Critical GetAwaiter() { return this; }
    public bool IsCompleted { get { return false; } }
    public void OnCompleted(Action k)
    { Console.WriteLine("Critical: OnCompleted"); k(); }
    public void UnsafeOnCompleted(Action k)
    { Console.WriteLine("Critical: UnsafeOnCompleted"); k(); }
    public void GetResult() { }
}

class App
{
    static async Task Use()
    {
        await new Plain();
        await new Critical();
        Console.WriteLine("both resumed");
    }

    static void Main() { Use().Wait(); }
}
