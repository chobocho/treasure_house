// 슬라이드 p6-v5-sm-hand — 손으로 쓴 상태 기계, C# 5.0
using System;
using System.Runtime.CompilerServices;

// AddLater as the compiler writes it, by hand
class Machine : IAsyncStateMachine
{
    public int state;                // -1 running, 0 waiting, -2 done
    public AsyncTaskMethodBuilder<int> builder;
    public int a, b;                    // parameters become fields
    TaskAwaiter<int> awaiter;

    public void MoveNext()
    {
        int result;
        try
        {
            if (state != 0)             // first entry
            {
                Console.WriteLine("  start, state " + state);
                awaiter = App.Gate.Task.GetAwaiter();
                if (!awaiter.IsCompleted)
                {
                    state = 0;
                    Machine me = this;
                    builder.AwaitUnsafeOnCompleted(ref awaiter, ref me);
                    return;             // suspend: back to the caller
                }
            }
            state = -1;                 // resumed (or never suspended)
            int bonus = awaiter.GetResult();
            Console.WriteLine("  resumed, bonus " + bonus);
            result = a + b + bonus;
        }
        catch (Exception e)
        { state = -2; builder.SetException(e); return; }
        state = -2;
        builder.SetResult(result);
    }

    public void SetStateMachine(IAsyncStateMachine m) { }
}
