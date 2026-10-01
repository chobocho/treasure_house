// 슬라이드 p6-v5-returnbad — return 에는 Task 가 아니라 값을, C# 5.0
using System.Threading.Tasks;

class App
{
    static async Task<int> Twice(int x)
    {
        await Task.FromResult(0);
        return Task.FromResult(x * 2);  // returning the Task itself
    }

    static async Task Done()
    {
        await Task.FromResult(0);
        return 1;                       // a value from a Task method
    }

    static void Main() { }
}
