// 슬라이드 p6-v5-awaitvoid — 결과 없는 await 는 값이 아니다, C# 5.0
using System.Threading.Tasks;

class App
{
    static async Task Demo()
    {
        var x = await Task.Delay(1);
    }

    static void Main() { }
}
