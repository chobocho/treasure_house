// 슬라이드 p6-v5-awaitname — async 안의 await 이름, C# 5.0
using System.Threading.Tasks;

class App
{
    static async Task<int> InAsync()
    {
        int await = 1;
        return await Task.FromResult(2);
    }

    static void Main() { }
}
