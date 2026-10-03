// 슬라이드 p11-v10-asyncbuilder — 호출을 찍는 빌더, C# 10.0
using System;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

// wraps the normal Task<T> builder and prints what the compiler calls
public struct LogBuilder<T>
{
    AsyncTaskMethodBuilder<T> inner;

    public static LogBuilder<T> Create()
    {
        Console.WriteLine($"  Create<{typeof(T).Name}>");
        var b = new LogBuilder<T>();
        b.inner = AsyncTaskMethodBuilder<T>.Create();
        return b;
    }
    public void Start<S>(ref S sm) where S : IAsyncStateMachine
    {
        Console.WriteLine($"  Start {typeof(S).Name}");
        inner.Start(ref sm);
    }
    public Task<T> Task => inner.Task;
    public void SetResult(T r)
    {
        Console.WriteLine($"  SetResult {r}");
        inner.SetResult(r);
    }
    public void SetException(Exception e) => inner.SetException(e);
    public void SetStateMachine(IAsyncStateMachine sm)
        => inner.SetStateMachine(sm);
    public void AwaitOnCompleted<A, S>(ref A a, ref S sm)
        where A : INotifyCompletion where S : IAsyncStateMachine
        => inner.AwaitOnCompleted(ref a, ref sm);
    public void AwaitUnsafeOnCompleted<A, S>(ref A a, ref S sm)
        where A : ICriticalNotifyCompletion where S : IAsyncStateMachine
        => inner.AwaitUnsafeOnCompleted(ref a, ref sm);
}
