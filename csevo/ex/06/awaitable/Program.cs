// 슬라이드 p6-v5-awaitable — 무엇이든 await 할 수 있다, C# 5.0
using System;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

// Not a Task: just the shape the compiler looks for
class Later
{
    public bool Done; public int Value; public Action Next;
    public LaterAwaiter GetAwaiter()
    {
        Console.WriteLine("  GetAwaiter");
        return new LaterAwaiter(this);
    }
    public void Complete(int v)
    {
        Value = v; Done = true;
        if (Next != null) Next();
    }
}

class LaterAwaiter : INotifyCompletion
{
    readonly Later l;
    public LaterAwaiter(Later l) { this.l = l; }
    public bool IsCompleted
    {
        get
        {
            Console.WriteLine("  IsCompleted " + l.Done);
            return l.Done;
        }
    }
    public void OnCompleted(Action k)
    {
        Console.WriteLine("  OnCompleted");
        l.Next = k;
    }
    public int GetResult()
    {
        Console.WriteLine("  GetResult");
        return l.Value;
    }
}
