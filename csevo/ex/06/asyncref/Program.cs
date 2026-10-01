// 슬라이드 p6-v5-asyncref — async 메서드의 ref·out 매개변수, C# 5.0
using System.Threading.Tasks;

class App
{
    static async Task TryRead(out int value)
    {
        await Task.Delay(1);
        value = 1;
    }

    static async Task Bump(ref int counter)
    {
        await Task.Delay(1);
        counter++;
    }

    static void Main() { }
}
