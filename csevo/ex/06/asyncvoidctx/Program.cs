// 슬라이드 p6-v5-asyncvoid-ctx — async void 는 문맥에 알린다, C# 5.0
using System;
using System.Threading;
using System.Threading.Tasks;

// A context that only reports; every call comes on Main's thread
class Spy : SynchronizationContext
{
    public override void OperationStarted()
    { Console.WriteLine("  ctx: OperationStarted"); }
    public override void OperationCompleted()
    { Console.WriteLine("  ctx: OperationCompleted"); }
    public override void Post(SendOrPostCallback d, object s)
    {
        try { d(s); }
        catch (Exception e)
        { Console.WriteLine("  ctx: Post threw " + e.Message); }
    }
}

class App
{
    static async void Handler(bool fail)
    {
        Console.WriteLine("Handler(" + fail + ") runs");
        await Task.FromResult(0);
        if (fail) throw new InvalidOperationException("boom");
    }

    static void Main()
    {
        SynchronizationContext.SetSynchronizationContext(new Spy());
        Handler(false);
        Handler(true);
        Console.WriteLine("Main: done");
    }
}
