import * as echarts from 'echarts/core';
import { PieChart } from 'echarts/charts';
import { TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([PieChart, TooltipComponent, CanvasRenderer]);

export function mountRecommendationChart(
  element: HTMLDivElement,
  data: Array<{ name: string; value: number }>,
) {
  const chart = echarts.init(element);
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: ['45%', '72%'],
        itemStyle: {
          borderRadius: 12,
          borderColor: '#f3efe5',
          borderWidth: 4,
        },
        label: { color: '#153243' },
        data,
      },
    ],
  });

  return () => chart.dispose();
}
