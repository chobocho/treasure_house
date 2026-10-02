// 슬라이드 p8-v7-tasktype-own — 컴파일러가 부르는 빌더, C# 7.0
using System;
using System.Runtime.CompilerServices;

public class LogBuilder<T>
{
    Box<T> box = new Box<T>();

    static void Log(string s) { Console.WriteLine("  builder." + s); }

    public static LogBuilder<T> Create()
    {
        Log("Create");
        return new LogBuilder<T>();
    }
    public void Start<TSM>(ref TSM sm) where TSM : IAsyncStateMachine
    {
        Log("Start");
        sm.MoveNext();               // run up to the first suspension
    }
    public void SetStateMachine(IAsyncStateMachine sm) { }
    public void SetResult(T r) { Log("SetResult " + r); box.Value = r; }
    public void SetException(Exception e)
    {
        Log("SetException " + e.Message);
        box.Error = e.Message;
    }
    public void AwaitOnCompleted<TA, TSM>(ref TA a, ref TSM sm)
        where TA : INotifyCompletion where TSM : IAsyncStateMachine
    { }
    public void AwaitUnsafeOnCompleted<TA, TSM>(ref TA a, ref TSM sm)
        where TA : ICriticalNotifyCompletion
        where TSM : IAsyncStateMachine
    { }
    public Box<T> Task { get { Log("Task"); return box; } }
}
