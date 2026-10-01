// 슬라이드 p6-v5-taskstatus — Task 의 상태들, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static void Main()
    {
        foreach (TaskStatus s in Enum.GetValues(typeof(TaskStatus)))
            Console.WriteLine("{0} {1}", (int)s, s);

        // what an async method's task goes through
        var gate = new TaskCompletionSource<int>();
        Func<Task<int>> f = async () => await gate.Task + 1;
        Task<int> t = f();
        Console.WriteLine("async task before: " + t.Status);
        gate.SetResult(1);
        Console.WriteLine("async task after:  " + t.Status);
    }
}
