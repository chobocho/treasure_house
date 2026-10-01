// 슬라이드 p6-v5-awaitbad — 모양이 모자라면, C# 5.0
using System;
using System.Threading.Tasks;

class NoFlag                            // no IsCompleted
{
    public NoFlag GetAwaiter() { return this; }
    public void OnCompleted(Action k) { }
    public void GetResult() { }
}

class NoInterface                       // not INotifyCompletion
{
    public NoInterface GetAwaiter() { return this; }
    public bool IsCompleted { get { return true; } }
    public void OnCompleted(Action k) { }
    public void GetResult() { }
}

class App
{
    static async Task A() { await new NoFlag(); }
    static async Task B() { await new NoInterface(); }
    static void Main() { }
}
